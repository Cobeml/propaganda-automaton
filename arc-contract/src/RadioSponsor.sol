// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

contract RadioSponsor is Ownable, ReentrancyGuard {
    struct Bid {
        address bidder;
        address token;
        uint256 amount;
        string transcript;
        BidStatus status;
        uint256 timestamp;
    }
    
    enum BidStatus {
        Pending,
        Accepted,
        Rejected
    }
    
    mapping(uint256 => Bid) public bids;
    uint256 public nextBidId;
    
    event BidSubmitted(
        uint256 indexed bidId,
        address indexed bidder,
        address indexed token,
        uint256 amount,
        string transcript
    );
    
    event BidAccepted(uint256 indexed bidId, address indexed bidder, address indexed token, uint256 amount);
    event BidRejected(uint256 indexed bidId, address indexed bidder, address indexed token, uint256 amount);
    
    constructor() Ownable(msg.sender) {
        nextBidId = 1;
    }
    
    function submitBid(address _token, uint256 _amount, string memory _transcript) external nonReentrant {
        require(_token != address(0), "Token address cannot be zero");
        require(_amount > 0, "Amount must be greater than 0");
        require(bytes(_transcript).length > 0, "Transcript cannot be empty");
        
        require(
            IERC20(_token).transferFrom(msg.sender, address(this), _amount),
            "Token transfer failed"
        );
        
        bids[nextBidId] = Bid({
            bidder: msg.sender,
            token: _token,
            amount: _amount,
            transcript: _transcript,
            status: BidStatus.Pending,
            timestamp: block.timestamp
        });
        
        emit BidSubmitted(nextBidId, msg.sender, _token, _amount, _transcript);
        nextBidId++;
    }
    
    function acceptBid(uint256 _bidId) external onlyOwner nonReentrant {
        Bid storage bid = bids[_bidId];
        require(bid.bidder != address(0), "Bid does not exist");
        require(bid.status == BidStatus.Pending, "Bid already processed");
        
        bid.status = BidStatus.Accepted;
        
        require(
            IERC20(bid.token).transfer(owner(), bid.amount),
            "Token transfer to owner failed"
        );
        
        emit BidAccepted(_bidId, bid.bidder, bid.token, bid.amount);
    }
    
    function rejectBid(uint256 _bidId) external onlyOwner nonReentrant {
        Bid storage bid = bids[_bidId];
        require(bid.bidder != address(0), "Bid does not exist");
        require(bid.status == BidStatus.Pending, "Bid already processed");
        
        bid.status = BidStatus.Rejected;
        
        require(
            IERC20(bid.token).transfer(bid.bidder, bid.amount),
            "Token refund failed"
        );
        
        emit BidRejected(_bidId, bid.bidder, bid.token, bid.amount);
    }
    
    function getBid(uint256 _bidId) external view returns (Bid memory) {
        return bids[_bidId];
    }
    
    function getPendingBidsCount() external view returns (uint256 count) {
        for (uint256 i = 1; i < nextBidId; i++) {
            if (bids[i].status == BidStatus.Pending) {
                count++;
            }
        }
    }
}